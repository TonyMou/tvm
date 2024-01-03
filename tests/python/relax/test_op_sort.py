# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import pytest
import tvm
import tvm.testing
from tvm import relax, tir
from tvm import TVMError
from tvm.ir import Op, VDevice
from tvm.script import relax as R


def test_op_correctness():
    x = relax.Var("x", R.Tensor((3, 4, 5), "float32"))
    assert relax.op.sort(x, axis=1).op == Op.get("relax.sort")


def _check_inference(bb: relax.BlockBuilder, call: relax.Call, expected_sinfo: relax.StructInfo):
    ret = bb.normalize(call)
    tvm.ir.assert_structural_equal(ret.struct_info, expected_sinfo)


def test_sort_infer_struct_info():
    bb = relax.BlockBuilder()
    vdev0 = VDevice("llvm")
    x0 = relax.Var("x", R.Tensor((2, 10, 4), "float32"))
    x1 = relax.Var("x", R.Tensor("float32", ndim=3))
    x2 = relax.Var("x", R.Tensor("float32"))
    x3 = relax.Var("x", R.Tensor((2, 10, 4)))
    x4 = relax.Var("x", R.Tensor(ndim=3))
    x5 = relax.Var("x", R.Tensor())
    x6 = relax.Var("x", R.Tensor((2, 10, 4), "float32", vdev0))

    _check_inference(bb, relax.op.sort(x0, axis=1), relax.TensorStructInfo((2, 10, 4), "float32"))
    _check_inference(
        bb, relax.op.sort(x6, axis=1), relax.TensorStructInfo((2, 10, 4), "float32", vdev0)
    )
    _check_inference(bb, relax.op.sort(x1, axis=1), relax.TensorStructInfo(dtype="float32", ndim=3))
    _check_inference(bb, relax.op.sort(x2, axis=1), relax.TensorStructInfo(dtype="float32"))
    _check_inference(bb, relax.op.sort(x3, axis=1), relax.TensorStructInfo((2, 10, 4), dtype=""))
    _check_inference(bb, relax.op.sort(x4, axis=1), relax.TensorStructInfo(dtype="", ndim=3))
    _check_inference(bb, relax.op.sort(x5, axis=1), relax.TensorStructInfo(dtype=""))
    _check_inference(bb, relax.op.sort(x0), relax.TensorStructInfo((2, 10, 4), "float32"))
    _check_inference(
        bb,
        relax.op.sort(x0, axis=1, descending=False),
        relax.TensorStructInfo((2, 10, 4), "float32"),
    )


def test_sort_infer_struct_info_shape_symbolic():
    bb = relax.BlockBuilder()
    a = tir.Var("a", "int64")
    b = tir.Var("b", "int64")
    c = tir.Var("c", "int64")
    x = relax.Var("x", R.Tensor((a, b, c), "float32"))

    _check_inference(bb, relax.op.sort(x, axis=1), relax.TensorStructInfo((a, b, c), "float32"))
    _check_inference(bb, relax.op.sort(x), relax.TensorStructInfo((a, b, c), "float32"))


def test_sort_infer_struct_info_more_input_dtype():
    bb = relax.BlockBuilder()
    x0 = relax.Var("x", R.Tensor((2, 3, 4), "float16"))
    x1 = relax.Var("x", R.Tensor((2, 3, 4), "int8"))

    _check_inference(bb, relax.op.sort(x0, axis=1), relax.TensorStructInfo((2, 3, 4), "float16"))
    _check_inference(bb, relax.op.sort(x1, axis=1), relax.TensorStructInfo((2, 3, 4), "int8"))


def test_sort_wrong_input():
    bb = relax.BlockBuilder()
    x0 = relax.Var("x", relax.ShapeStructInfo((2, 3, 4, 5)))
    x1 = relax.Var("x", relax.FuncStructInfo([], R.Tensor((2, 3, 4, 5), "float32")))
    x = relax.Var("x", R.Tensor((3, 4, 5), "float32"))
    y = relax.Var("y", R.Tensor((2, 3, 4), "float32"))

    with pytest.raises(TVMError):
        relax.op.sort(x, y)

    with pytest.raises(TVMError):
        bb.normalize(relax.op.sort(x0, axis=1))

    with pytest.raises(TVMError):
        bb.normalize(relax.op.sort(x1, axis=1))


if __name__ == "__main__":
    tvm.testing.main()
